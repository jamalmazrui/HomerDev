---
name: homer-books
description: >-
  Builds, audits and publishes Kindle books with the HomerDev kit's book tools,
  in a Homer book publishing project: a catalog in configs\books.inix, each
  book's sources in its own folder under books, EPUBs and audits in results,
  and KDP's records in data. Covers the catalog's keys, the build settings, KDP's
  tables of contents, EPUBCheck, Ace and Kindle Previewer checks, AI and
  accessibility answers, and sending updates with kdpUpdate. Use this skill
  whenever the user wants to build, check, convert, publish, update or submit a
  book, ebook, EPUB or Kindle title; asks about KDP, a book's catalog entry,
  its audit, its AI disclosure or its cover; or starts a new book project,
  even if they do not name the kit's tools.
---

# Homer book publishing

A Homer project publishes books when `configs\books.inix` exists. The kit's
`kind` script reports it. The full pattern is the kit's `help\BookPattern.md`;
read it before changing a book project's layout or settings.

## Where things are

- `books\<root>\<root>.md` -- each book's manuscript, with any `.bib`, `.csl`,
  `.jpg` cover, `.css` and `images` folder beside it. The root is the title
  with a leading A, An or The dropped and the other words joined by underscores.
- `configs\books.inix` -- the catalog; `configs\buildBooks.inix` -- build
  settings, including the project's own `author`; `configs\<root>_KDP.inix` --
  a new book's KDP answers.
- `results` -- each EPUB and its audit. `data\books` and `data\receipts` --
  what KDP holds, and what was uploaded and submitted. Never overwrite `data`
  from outside: it is the record of what the author's runs did.

## The tools, and their order

1. `scripts\buildBooks` builds and audits every book, or those named with
   `--book`. Read `results\<root>-audit.md`: a book is ready only when it says
   so, and the audit names the EPUB it approved by its SHA-256 fingerprint.
2. `scripts\kdpBooks --export` reads every book's KDP details into `data\books`.
3. `scripts\kdpUpdate` sends each ready, changed book to its KDP title.
   `--book` limits it; `--no-publish` stops at a saved draft; `--republish`
   sends unchanged books too. A book KDP is reviewing is skipped, not failed.
4. `scripts\kdpSubmit --book <root>` submits a new book from its answers file.

The code originates in the kit's `scripts` folder; each wrapper copies the
kit's current tools in before running. Fix a tool in the kit, never in a
project's copy, or the next run will replace the fix.

## Rules that protect the author

- A book's manuscript and cover are commercial: never upload or change them on
  KDP, or push a manuscript to a public repository, without the author's
  explicit permission.
- AI answers never disclose less than KDP already holds, unless the author has
  confirmed an answer (`aiConfirmed`). Ask the author; never guess what AI made.
- The tools hold no personal data. Names, folders, title IDs and answers belong
  in the project's `configs` and `data`, never in a script.
- Claims inside the EPUB are only what the build can stand behind: no
  conformance claim or certification, and pictures are said to have text
  alternatives only when every one has.

## When something fails

Every run writes a detailed log in `logs`. Read it before changing code: the
log names each command, its exit code and what KDP or a checker said. Kindle
Previewer's Enhanced Typesetting verdict is not always repeatable, so the build
confirms an unsupported verdict with a second run before reporting it.
