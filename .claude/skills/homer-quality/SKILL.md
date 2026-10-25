---
name: homer-quality
description: >-
  Checks a document for accessibility and quality the Homer way, and says what
  to fix: Word, Excel, PowerPoint, Markdown, web pages, EPUB and PDF, by the
  rules extCheck reports, the HomerDev kit's finishing checks (title, author,
  language, headings, picture descriptions, table headers, workbook header
  names, tagged PDF) and WCAG 2.2 AA. Use when the user asks whether a file is
  accessible, wants a document, book, spreadsheet, slide deck or PDF checked or
  audited, asks why a screen reader reads a file badly, or wants a file a Homer
  app made verified before sending it. Not for an app's own documents (use
  homer-docs) or a Kindle book's full audit (use homer-books).
---

# Checking a document's quality

Every file a Homer app makes is already finished for a screen reader and checked
(help\Conversions.md, "Every File Finished for a Screen Reader"). This skill is
the same checking, on any file: one a person wrote, one from elsewhere, or one a
Homer app made that should be verified before it is sent.

## Run the checker

`scripts\checkQuality.cmd <file or folder> ...` checks every Word, Excel,
PowerPoint, Markdown, web page, EPUB and PDF file it is given, and every one in a
folder given. It never changes a file: each is checked through a copy. For each
file it lists findings in two groups:

- **Would fix:** what the kit's finishing step fixes by itself when a Homer app
  makes the file -- a missing title, author or language, workbook header names,
  a frozen header row, a table's header row, front matter, an EPUB's
  accessibility metadata.
- **Needs a person:** what only a person can decide -- a picture without a
  description, a document without headings, a skipped heading level, a slide
  without a title, merged cells, an untagged PDF, a PDF without bookmarks.

It exits 0 when nothing needs a person, 1 when something does, 2 when it could
not run. Its log, in logs\checkQuality-<time>.log beside where it ran, names its
environment and every finding.

## The rules, and where each lives

- **Word, Excel and PowerPoint:** extCheck's rules, read from each file's XML,
  are in the kit's Quality.cs (OfficeCheck) and judge every file a C# Homer app
  makes. Color used alone and Word's own help text for a form field need Office
  and stay in extCheck; run extCheck for those.
- **Markdown:** all of extCheck's Markdown rules (MarkdownCheck in Quality.cs),
  and one H1 per document.
- **Web pages:** the Homer page form -- one H1, main, lang and title -- and
  pictures without alt text.
- **EPUB:** title and language, EPUB Accessibility 1.1 metadata that claims only
  what is true; for a book, buildBooks also runs DAISY's Ace and EPUBCheck.
- **PDF:** a structure tree, the marked-content flag, a language, a title and
  bookmarks. A PDF can hide its tags in a compressed stream, so listen to one
  before calling it untagged.
- **Workbooks:** header names JAWS and NVDA read (ColumnTitle, RowTitle, Title),
  from the author's xlHeaders, improved; columns laid out for reading, from
  xlFormat.

The checker in Python runs the kit's Python checks; the C# apps add the whole of
extCheck's Markdown and Office rules from Quality.cs. For the fullest report on
an Office file, run extCheck itself.

## Fixing what is found

- A finding the kit would fix is fixed by converting the file with any Homer app
  (BatCon, to the same type through another, or the kit's Conversion).
- A picture description says in a sentence what the picture shows; never a file
  name, never "Photo of".
- A heading is a heading style, not bold text; a table's first row is its header
  row.
- Report findings with the rule's name, as extCheck does, so a report reads the
  same from every tool.
