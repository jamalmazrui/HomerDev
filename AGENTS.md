# AGENTS.md -- the Homer Development Kit, for AI agents

HomerDev is a development kit for building Windows programs, documents, books, databases, installers and spoken tutorials for people who use screen readers. It holds shared code in C# and Python, templates, build and release scripts, checks, and twenty skills that state its conventions. Its programs are used with a keyboard and a screen reader -- JAWS, NVDA or Narrator -- so every rule serves one aim: the person hears each thing once, in the order they meet it, and can reach any command by a key they can guess.

This file is for any AI agent asked to use the kit. Read it first; then read the skill that matches the task before writing anything.

## Using the kit from another project

- **Finding the kit.** The `HomerDev` environment variable names its folder; HomerDev_setup.exe installs it to `C:\Program Files\HomerDev`, and developers often keep it at `C:\HomerDev`. `scripts\kind --kit` prints the folder it finds. Read files there directly; do not ask the person where the kit is.
- **Connected once.** `scripts\connectAI` (also the HomerDev dialog's Connect AI tools button) puts a pointer to the kit in the personal instruction file of Claude Code, Codex and Gemini CLI or Antigravity, and links the kit's skills into each tool's personal skills folder. When the person mentions Homer or HomerDev, read this file, then the matching skill.

- **Claude Code, as a plugin.** `/plugin marketplace add JamalMazrui/HomerDev`, then `/plugin install homer-dev@homer-dev-kit`. The skills and the two subagents then work in any project, named `homer-dev:<skill>`.
- **Any agent, from the installer or the repository.** Run HomerDev_setup.exe from the latest release, or download `https://github.com/JamalMazrui/HomerDev/archive/main.zip` (HomerDev-main.zip) and unzip it to `C:\HomerDev`; Homer apps build against that folder and never need it once installed. `newHomerApp` starts an app; `updateAppBuilds` refreshes the kit's scripts in every app.
- **Only some parts.** Every skill, shared class and template stands on its own and may be used alone; each skill's SKILL.md names the files it relies on.

## Where things are

- `exec/CSharp/` and `exec/Python/` -- the shared code: Lbc dialogs, Say (speech through any screen reader), Log, Inix settings, Elevate (updates), the Homer Player, Mdi windows, Paths, Web, Ollama.
- `Templates/` -- a new app's starting files: source, build script, installer (`_APP__setup.iss` with `HomerComponents.iss`), acceptance checks, and the ten tutorial walks.
- `scripts/` -- the build, check, tidy, push, release, conversion, tutorial and book tools every app shares.
- `help/` -- the kit's documents: `HomerDev.md` (the guide), `Developer.md`, `FinishPage.md`, `Logging.md`, `Inix.md`, `BookPattern.md`, the Camel Type guides, `Hotkeys.md`, `History.md`.
- `.claude/skills/` -- the skills, one folder each, a `SKILL.md` with its rules and often `references/` and `scripts/`.
- `.claude/agents/` -- the subagents.

## Skills: which to read for which task

Each skill holds the rules for one kind of work. Claude loads a skill by its description; other agents should open the matching SKILL.md before the task. When a task spans several, read each.

- **app-help-guide** -- build a screen-reader-friendly help guide for a product from the publisher's own help pages. `.claude/skills/app-help-guide/SKILL.md`
- **blind-creators** -- add, verify or remove a person or work in the Blind Authors, Developers, Presenters or Creators directories. `.claude/skills/blind-creators/SKILL.md`
- **convention-database** -- build a DbDo database of any organization's convention or conference from its agenda: sessions, rooms, speakers and sponsors, linked. `.claude/skills/convention-database/SKILL.md`
- **readable-text** -- edit machine text -- captions, transcripts, OCR output, hard-wrapped or escaped text -- into readable, faithful prose, marking doubt rather than guessing and saying where the words came from. `.claude/skills/readable-text/SKILL.md`
- **homer-books** -- build, audit and publish Kindle books with the kit's book tools. `.claude/skills/homer-books/SKILL.md`
- **homer-build-release** -- run or troubleshoot build, tidy, push and release, with the checks inside them, and read their logs. `.claude/skills/homer-build-release/SKILL.md`
- **homer-code** -- write or review code in Camel Type with the kit's shared classes. `.claude/skills/homer-code/SKILL.md`
- **homer-convert** -- convert documents and data between formats, writing the Homer encoding. `.claude/skills/homer-convert/SKILL.md`
- **homer-db** -- design or check a SQLite database the way DbDo opens it. `.claude/skills/homer-db/SKILL.md`
- **homer-library-source** -- add a book library, such as Apple Books, to bookFido, or a source to any harvester. `.claude/skills/homer-library-source/SKILL.md`
- **homer-docs** -- write or review an app's documents at a ninth-grade reading level. `.claude/skills/homer-docs/SKILL.md`
- **homer-elevate** -- add or fix F11, Elevate Version, the update check. `.claude/skills/homer-elevate/SKILL.md`
- **homer-installer** -- write or fix an Inno Setup installer and its finish page. `.claude/skills/homer-installer/SKILL.md`
- **homer-migrate** -- bring an existing app onto the kit, or audit one that has drifted. `.claude/skills/homer-migrate/SKILL.md`
- **homer-new-app** -- start a new app from the kit's templates. `.claude/skills/homer-new-app/SKILL.md`
- **homer-page** -- publish a document as an accessible GitHub Page. `.claude/skills/homer-page/SKILL.md`
- **homer-screen-reader** -- write or install JAWS scripts and NVDA add-ons. `.claude/skills/homer-screen-reader/SKILL.md`
- **homer-tutorial** -- write or check the spoken walkthroughs, where a host works and a screen reader answers. `.claude/skills/homer-tutorial/SKILL.md`
- **homer-ui** -- design dialogs, menus, keys and speech for screen reader users. `.claude/skills/homer-ui/SKILL.md`
- **podcast-directory** -- build a screen-reader-friendly directory of a podcast from its RSS feed. `.claude/skills/podcast-directory/SKILL.md`

## Subagents

Each works in its own context and returns a short report, so a long, read-heavy review does not crowd the main conversation. Claude Code runs them by name; another agent can follow the same procedure from the file.

- **homer-auditor** -- audits one or more projects against the kit -- installer pattern, tutorials, encoding, checks -- and reports every departure without changing anything. `.claude/agents/homer-auditor.md`
- **homer-listener** -- reads tutorial walks as a screen reader user hears them, against the app's real announcements, and reports every reader line a screen reader would not actually say. `.claude/agents/homer-listener.md`

## Rules every agent follows

- **Camel Type** for code: Hungarian prefixes (`sPath`, `bFound`, `lsFiles`), lower camel case, one statement per line, declarations alphabetical. The homer-code skill has it all.
- **The Homer encoding**: UTF-8 with a byte order mark and CRLF line endings, except the files `KeepEncoding.txt` lists, `.cmd` and `.bat` files, `version.txt` and `SKILL.md`.
- **Detailed logs** from every script and build: environment, settings, every command with its exit code, every error. The console stays brief.
- **Screen reader agnostic**: no screen reader's own vocabulary in an app's speech or documents; a tutorial names no screen reader.
- **The cycle**: in `C:\<App>`, `build_release` runs build, then `scripts\tidy`, `scripts\push` and `scripts\release`, stopping at the first that fails; push runs the project's check before it stages anything, and release again before it tags, so nothing broken is pushed. The kit's build writes it into every project from `scripts\build_release.cmd`. A fix must work through those steps; repairs to a machine's state go in the build, never in a separate script for the person to run.
- **Checks decide**: `build.py check` for the kit, `scripts\check.py` in an app (which includes the installer pattern), `scripts\checkTutorial.py` for walks. A change is done when they pass.
- **Deliver whole files**, as the project's zip, never as editing instructions.
