---
name: homer-code
description: >-
  Writes and reviews code for Homer Tools apps and the Homer Development Kit
  in Camel Type, Jamal Mazrui's screen-reader-oriented style, in C#, Python,
  JavaScript, VBScript or JAWS script, using the kit's shared C# classes and
  Python modules rather than custom code. Use when writing, porting, fixing or
  reviewing any Homer program, script or build helper, or when asked about
  Camel Type, Hungarian prefixes, the kit's Log, Say, Lbc, Inix, Web, Paths or
  KeyMap, or how Homer files are encoded.
---

# Homer code

Code is written to be read by ear. A screen reader user hears `sPath`,
`bFound`, `lsFiles` and knows each type without seeking back to a declaration;
one complete statement per line; lists and names in alphabetical order.

## The rules that matter most

- **Hungarian prefixes** on every variable, argument, field and constant: `a`
  array, `b` boolean, `bin` binary buffer, `d` dictionary, `dt` date-time, `f`
  file, `h` handle, `i` integer, `ls` list, `n` real, `s` string, `v` variant.
  Another object takes its class name in lower camel case (`form`, `writer`)
  or a common abbreviation (`sb`, `pd`); in C#, `o` is for COM objects only.
- **Constants** add `c_` in front: `c_sFormat`, `c_iMaxRetries`. No magic
  numbers: use the language's own constant, or define one.
- **Lower camel case** for everything the program names, functions and
  methods included, wherever the language allows.
- **Functions, never subroutines**: a routine returns something even when the
  result does not matter (`return true`).
- **A simple if and its consequence on one line.**
- **For-each loops** over collections rather than index loops, where the
  language allows.
- **Declarations at the top** of the program or function, one type per line,
  names alphabetical on the line, the lines themselves alphabetical by type;
  constants the same, before the variables.
- **Double quotes** for strings where either quote works.
- **Imports**: Python has two lines, standard library then third party, each
  alphabetical; JavaScript has one require or import per module, alphabetical.
- **Every CLI program and script writes a detailed log** (environment,
  settings, each command with its exit code, any error) through the kit's
  `Log` or `log`, never only a console message. The console stays short.

The full rules, with examples, are in the style references below. When porting
from another language, keep the original names first, then render them in
Camel Type.

## Encoding

Every text file is UTF-8 with a byte order mark and CRLF line endings, except
`.cmd` and `.bat` (CRLF, no mark) and each skill's SKILL.md (no mark, since
its first characters must be its front matter). Files a program writes follow
the same rule: in Python, `open(sPath, "w", encoding="utf-8-sig",
newline="\r\n")`. Files a program reads are decoded with the Ude detection the
kit already has, never assumed.

## Build on the kit

A Homer program uses the kit's shared code rather than its own: `Lbc` for
every dialog, `Log` for its log, `Say` for speech, `Inix` for settings (a file Homer creates is always `.inix`, never `.ini`, which is only for another program that requires it),
`Paths` for its folders, `Web` for downloads, `KeyMap` and `KeyName` for keys,
`Util` for the small helpers, `Media` (or `media.py`) to find a shared tool. The more they are exercised, the better they
get. Read [references/kit-libraries.md](references/kit-libraries.md) for what
each offers and how an app compiles or imports it.

**Fix a fault where it starts.** When an app's problem comes from a shared
class -- focus order from Lbc, speech from Say -- fix the class in the kit,
not the app, so every app gains the fix at its next build.

**Find a shared tool by its newest copy, never the first on the PATH.**
A machine may hold several copies of Pandoc, Java or ExifTool, and an old one
early on the PATH (an author's C:\bin\pandoc.exe, 2.19.2) hides the current
one. A Python script asks `media.newestInstalled` or `media.pandocProgram`; a
cmd script reads the path the kit's `scripts\newest.ps1` prints, as the build
templates do. Give a minimum version when an older one would fail.

**A change to what is heard is tried with the readers.** When a change
alters what a screen reader says or which keys do what, it is tried with JAWS
and with NVDA before release. The kit's checks prove the rules they test;
only a screen reader proves what a person hears.

## Style references

Read the one for the language at hand:

- C#: [references/CamelType_CSharp.md](references/CamelType_CSharp.md), with
  the quick reference [references/CamelType_CSharp_Reference.md](references/CamelType_CSharp_Reference.md)
- Python: [references/CamelType_Python.md](references/CamelType_Python.md)
- JAWS script: [references/CamelType_JAWSScript.md](references/CamelType_JAWSScript.md)
- Logging, where each log goes and what it is called:
  [references/Logging.md](references/Logging.md)

These five are copied from the kit's `help` folder each time the kit is
built, so they are the kit's current rules.
