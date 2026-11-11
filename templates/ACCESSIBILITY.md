# Accessibility

<!-- Template from the Homer Development Kit. Replace every line in angle brackets. GitHub shows this file as an Accessibility tab on the repository's front page when it sits in .github, the root, or docs. Keep it short and true; a statement that exists beats a template never filled in. -->

<APP> is <one sentence: what it does and who it is for>. It is built by a screen reader user for screen reader users, so every command works from the keyboard and speaks what the screen reader cannot know by itself.

## What we aim for

- Every control has a name and a role, and a value or state where it needs one; nothing is shown by color alone.
- Every task can be done from the keyboard; the hotkeys are listed in `help\Hotkeys.md`.
- Spoken messages add only what the screen reader does not already say.
- The target is WCAG 2.2 AA where it applies to a desktop program, and the Homer Accessibility Rules.

## Tested with

- <JAWS version> and <NVDA version> on <Windows version>, by <who>, on <date>, with <speech, braille, or both>. A screen reader presents the screen as speech, as braille on a refreshable display, or both; say which you tested.
- <Any other screen reader, platform or automated check, or "no automated accessibility scan has been run yet".>

## Known barriers

- <One line per barrier: what does not work, with which screen reader, and whether a fix is planned.>

## Reporting a barrier

Open an issue in this repository using the bug report form in `templates\Bug_Report.md`: one problem per report, the steps from where focus was, what you expected to hear, and what you heard, quoted from the screen reader.

## Ownership

<Name> maintains this project. This statement was written on <date> and is revised with each release.
