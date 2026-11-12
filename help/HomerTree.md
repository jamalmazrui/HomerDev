---
title: "The Homer Tree"
author: "Jamal Mazrui"
---

# The Homer Tree

Every Homer project keeps the same folders and files, so you find anything by name, and one letter takes you to each folder. This page names each entry and says what it is for. The kit's kind.py holds the same lists, and check fails a project that drifts from them.

## Rules

- **One letter, one folder.** No two top-level folders share a first letter, so first-letter navigation lands exactly.
- **No new folders unasked.** A folder not named here goes to notes, unless the project's RepoFiles.txt or LocalFiles.txt names it.
- **Subfolders are free.** Nest inside a standard folder, such as data\harvests or notes\retired.
- **De facto names win.** Where a tool or industry expects a name, such as .github, AGENTS.md or _config.yml, Homer uses it.
- **One source.** A document, script or setting lives in one place. Kit tools are copied into a project's scripts folder by its build, never edited there.

## Folders

- **books:** each book's sources, one folder per book. Book projects only.
- **configs:** settings that decide how a program or script starts, in .inix.
- **data:** databases, seed data, and anything kept between sessions, such as data\harvests.
- **exec:** the built program and its libraries. Apps and the kit only; never pushed.
- **help:** every document besides the ReadMe and License: the guide, Developer, History, Hotkeys, tutorials.
- **logs:** one log per run, named <Project>-<task>-yyyyMMdd-HHmmss.log; never pushed.
- **notes:** files kept on this disk but never pushed or installed; tidy puts strays here, and notes\retired holds what a build retired.
- **pages:** one folder per GitHub Page. Pages projects only.
- **results:** outputs, such as built books or harvest archives. Nothing reads them again, so they may be moved away.
- **scripts:** scripts, add-ons and plugins: the project's own and the kit tools its build refreshes.
- **templates:** files a person copies and fills in. The only folder starting with t.
- **work:** scratch. Each new session may delete what an earlier one left.

Page projects may also have **_data**, **_includes**, **_layouts** and **assets**, the names GitHub Pages expects. Python's **build** and **dist** output folders may appear too; git never takes them, and tidy and the audit pass them by.

## Hidden folders

- **.claude:** skills and agents for Claude and other agents that read the same layout.
- **.claude-plugin:** the plugin manifest that shares those skills.
- **.git:** the repository.
- **.github:** Copilot instructions and GitHub settings.
- **.vs, .vscode:** an editor's own state; never pushed.

## Files at the top

- **.gitattributes, .gitignore:** git's rules; tidy writes .gitignore from LocalFiles.txt.
- **<App>.cs, <App>.py:** an app's source, named for its folder.
- **<App>.ico, <App>_setup.iss:** an app's icon and installer script.
- **_config.yml:** a GitHub Page's site settings. Page projects only.
- **ACCESSIBILITY.md:** the accessibility statement GitHub shows as a tab.
- **AGENTS.md, CLAUDE.md, GEMINI.md, llms.txt:** what AI agents read first, by each tool's convention.
- **build.cmd:** an app's or the kit's build. Other projects have none; the kit builds them by role.
- **create<App>Repo.cmd, .ps1:** the maintainer script that makes an app's repository; kept at the top, never pushed.
- **build_release.bat:** the cycle: build, tidy, push, release.
- **KeepEncoding.txt:** files fixEncoding leaves as they are.
- **License.md, License.htm:** the license: MIT for code, CC BY-SA 4.0 for writing.
- **LocalFiles.txt:** what belongs on this disk but never in the repository.
- **ReadMe.md, ReadMe.htm:** the quick start.
- **RepoFiles.txt:** what push puts on GitHub; tidy needs it to know what belongs.
- **version.txt:** an app's or the kit's version.

A collection's documents, each .md with its .htm, sit at the top too. So does a page project's own page, <Folder>.md.

## Kinds and roles

- **app:** builds a program and its installer; releases on GitHub.
- **books:** MyBooks; builds with buildBooks, releases with kdpSubmit.
- **guides:** AppHelpGuides; builds changed guides; the push publishes them.
- **kit:** HomerDev; builds, checks and releases itself.
- **pages:** MyPages; nothing to compile; releases with post.
- **podcasts:** PodcastDirectories; rebuilds changed pages; the push publishes them.

## The two installed trees

- **%ProgramFiles%\\<App>:** configs, data, exec, help, scripts, templates, and the ReadMe and License. Read-only.
- **%LOCALAPPDATA%\\<App>:** configs, data, logs, results, scripts, work. The program writes only here, never under %APPDATA%.
